import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

function fmtDate(v) {
  if (!v) return "—";
  try {
    return new Date(v).toLocaleString();
  } catch {
    return "—";
  }
}

function money(v) {
  const n = Number(v);
  if (Number.isNaN(n)) return String(v ?? "—");
  return n.toLocaleString();
}

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.rows)) return data.rows;
  return [];
}

function getCount(node) {
  const v =
    node?.items_count ??
    node?.itemsCount ??
    node?.count ??
    node?.products_count ??
    node?.productsCount ??
    null;

  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function CategoryRow({ node, level, isOpen, hasChildren, onToggle, onPick, selected }) {
  const cnt = getCount(node);

  return (
    <div className={`catRow ${selected ? "selected" : ""}`} style={{ paddingLeft: 10 + level * 16 }}>
      <button
        className="catTwisty"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (hasChildren) onToggle(node);
        }}
        title={hasChildren ? (isOpen ? "Свернуть" : "Развернуть") : "Нет подкатегорий"}
      >
        {hasChildren ? (isOpen ? "▾" : "▸") : "•"}
      </button>

      <button className="catPick" onClick={() => onPick(node)} title="Выбрать категорию">
        <span className="catLeft">
          <span className="catName">{node.title}</span>
        </span>

        <span className="catRight">
          {cnt !== null ? <span className="countBadge">{cnt}</span> : null}
          <span className="catMeta">ID {node.id}</span>
        </span>
      </button>
    </div>
  );
}

export default function CatalogManager({ notify }) {
  const [shops, setShops] = useState([]);
  const [shopId, setShopId] = useState("");

  const [nodesById, setNodesById] = useState(new Map());
  const [childrenByParent, setChildrenByParent] = useState(new Map());
  const [loadedParents, setLoadedParents] = useState(new Set());
  const [openIds, setOpenIds] = useState(new Set());

  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [items, setItems] = useState([]);

  const [catTitle, setCatTitle] = useState("");
  const [catImg, setCatImg] = useState(""); 
  const [itemTitle, setItemTitle] = useState("");
  const [itemPrice, setItemPrice] = useState("");
  const [itemDesc, setItemDesc] = useState("");
  const [itemImg, setItemImg] = useState("");

  const [treeLoading, setTreeLoading] = useState(false);

  const selectedCategory = useMemo(() => {
    if (!selectedCategoryId) return null;
    return nodesById.get(Number(selectedCategoryId)) || null;
  }, [nodesById, selectedCategoryId]);

  const shopTitle = useMemo(() => {
    const s = shops.find((x) => String(x.id) === String(shopId));
    return s?.title ?? "";
  }, [shops, shopId]);

  function parentKey(pid) {
    return pid == null ? "root" : String(pid);
  }

  function isParentLoaded(id) {
    return loadedParents.has(parentKey(id));
  }

  async function loadShops() {
    try {
      const data = await api("/api/superadmin/shops");
      const list = normalizeList(data);
      setShops(list);
      if (!shopId && list?.[0]?.id) setShopId(String(list[0].id));
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function loadCategories(parentId) {
    if (!shopId) return [];

    const p = new URLSearchParams({ shop_id: String(shopId) });
    if (parentId !== null && parentId !== undefined) p.set("parent_id", String(parentId));

    try {
      const data = await api(`/api/catalog/categories?${p.toString()}`);
      const list = normalizeList(data);

      setNodesById((prev) => {
        const m = new Map(prev);
        for (const c of list) m.set(Number(c.id), c);
        return m;
      });

      setChildrenByParent((prev) => {
        const m = new Map(prev);
        const key = parentId == null ? "root" : String(parentId);
        m.set(key, list.map((c) => Number(c.id)));
        return m;
      });

      setLoadedParents((prev) => {
        const s = new Set(prev);
        s.add(parentId == null ? "root" : String(parentId));
        return s;
      });

      return list;
    } catch (e) {
      notify?.("Ошибка", e.message);
      return [];
    }
  }

  async function loadItems() {
    if (!shopId || !selectedCategoryId) {
      setItems([]);
      return;
    }
    try {
      const p = new URLSearchParams({
        shop_id: String(shopId),
        category_id: String(selectedCategoryId),
      });
      const data = await api(`/api/catalog/items?${p.toString()}`);
      setItems(normalizeList(data));
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  useEffect(() => {
    loadShops();
  }, []);

  useEffect(() => {
    if (!shopId) return;

    setNodesById(new Map());
    setChildrenByParent(new Map());
    setLoadedParents(new Set());
    setOpenIds(new Set());
    setSelectedCategoryId(null);
    setItems([]);

    loadCategories(null);
  }, [shopId]);

  useEffect(() => {
    loadItems();
  }, [shopId, selectedCategoryId]);

  async function toggleNode(node) {
    const id = Number(node.id);

    if (!isParentLoaded(id)) {
      await loadCategories(id);
    }

    setOpenIds((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return s;
    });
  }

  function pickCategory(node) {
    setSelectedCategoryId(Number(node.id));
  }

  const flatTree = useMemo(() => {
    const out = [];
    const roots = childrenByParent.get("root") || [];

    function dfs(id, level) {
      const node = nodesById.get(Number(id));
      if (!node) return;

      const childIds = childrenByParent.get(parentKey(id)) || [];
      const open = openIds.has(Number(id));
      const hasChildren = childIds.length > 0 || !isParentLoaded(Number(id));

      out.push({ node, level, open, hasChildren });

      if (open) for (const cid of childIds) dfs(cid, level + 1);
    }

    for (const rid of roots) dfs(rid, 0);
    return out;
  }, [childrenByParent, nodesById, openIds, loadedParents]);

  function collapseAll() {
    setOpenIds(new Set());
  }

  async function expandAll() {
    if (!shopId) return;
    setTreeLoading(true);

    try {
      const roots = await loadCategories(null);
      const queue = roots.map((c) => Number(c.id));

      const loadedKey = new Set();
      loadedKey.add("root");

      const openSet = new Set();

      while (queue.length) {
        const id = queue.shift();
        if (!id) continue;

        openSet.add(id);

        const k = parentKey(id);
        if (loadedKey.has(k)) continue;

        const children = await loadCategories(id);
        loadedKey.add(k);

        for (const ch of children) queue.push(Number(ch.id));
      }

      setOpenIds(openSet);
    } finally {
      setTreeLoading(false);
    }
  }

  async function createCategory() {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    if (!catTitle.trim()) return notify?.("Ошибка", "Введите название категории");

    if (!catImg.trim()) return notify?.("Ошибка", "Добавьте картинку категории (URL)");

    try {
      await api("/api/catalog/categories", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          title: catTitle.trim(),
          img: catImg.trim(),
          parent_id: selectedCategoryId ? Number(selectedCategoryId) : null,
        },
      });

      setCatTitle("");
      setCatImg("");
      notify?.("Готово", selectedCategoryId ? "Подкатегория создана" : "Категория создана");

      const pid = selectedCategoryId ? Number(selectedCategoryId) : null;
      await loadCategories(pid);
      if (pid) setOpenIds((prev) => new Set(prev).add(pid));
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function deleteSelectedCategory() {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    if (!selectedCategoryId) return notify?.("Ошибка", "Выберите категорию слева");

    const ok = window.confirm("Удалить категорию?\n\nВажно: в категории не должно быть товаров и подкатегорий.");
    if (!ok) return;

    try {
      const p = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/categories/${Number(selectedCategoryId)}?${p.toString()}`, { method: "DELETE" });

      notify?.("Готово", "Категория удалена");
      setSelectedCategoryId(null);
      await loadCategories(null);
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function createItem() {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    if (!selectedCategoryId) return notify?.("Ошибка", "Сначала выберите категорию слева");
    if (!itemTitle.trim()) return notify?.("Ошибка", "Введите название товара");

    if (!itemImg.trim()) return notify?.("Ошибка", "Добавьте ссылку на картинку товара");

    const price = Number(String(itemPrice).replace(/[^\d]/g, ""));
    if (Number.isNaN(price)) return notify?.("Ошибка", "Введите цену");

    try {
      await api("/api/catalog/items", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          category_id: Number(selectedCategoryId),
          title: itemTitle.trim(),
          price,
          description: itemDesc?.trim() ? itemDesc.trim() : null,
          img: itemImg.trim(),
        },
      });

      setItemTitle("");
      setItemPrice("");
      setItemDesc("");
      setItemImg("");

      notify?.("Готово", "Товар добавлен");
      await loadItems();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function deleteItem(itemId) {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    const ok = window.confirm("Удалить этот товар?");
    if (!ok) return;

    try {
      const p = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/items/${Number(itemId)}?${p.toString()}`, { method: "DELETE" });
      notify?.("Готово", "Товар удалён");
      await loadItems();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "end" }}>
        <div>
          <h2 style={{ margin: 0 }}>Каталог</h2>
          <div className="muted" style={{ marginTop: 6 }}>
            {shopTitle ? (
              <>
                Магазин: <b>{shopTitle}</b>
              </>
            ) : (
              "Выберите магазин, чтобы управлять каталогом"
            )}
          </div>
        </div>

        <div className="field" style={{ minWidth: 320 }}>
          <label>Магазин</label>
          <select value={shopId} onChange={(e) => setShopId(e.target.value)}>
            {shops.map((s) => (
              <option key={s.id} value={String(s.id)}>
                {s.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="hr" />

      <div className="catalogGrid">
        <div className="catalogCol">
          <div className="panelTitle">Категории</div>

          <div className="row" style={{ marginBottom: 10 }}>
            <button className="btn ghost" onClick={expandAll} disabled={!shopId || treeLoading}>
              {treeLoading ? "Разворачиваю…" : "Развернуть всё"}
            </button>
            <button className="btn ghost" onClick={collapseAll} disabled={!shopId || treeLoading}>
              Свернуть всё
            </button>
          </div>

          <div className="catBox">
            {flatTree.map(({ node, level, open, hasChildren }) => (
              <CategoryRow
                key={node.id}
                node={node}
                level={level}
                isOpen={open}
                hasChildren={hasChildren}
                onToggle={toggleNode}
                onPick={pickCategory}
                selected={Number(selectedCategoryId) === Number(node.id)}
              />
            ))}

            {!flatTree.length ? (
              <div className="muted" style={{ padding: 12 }}>
                Пока нет категорий
              </div>
            ) : null}
          </div>

          <div className="hr" />

          <div className="panelTitle">Выбранная категория</div>
          <div className="muted" style={{ marginBottom: 8 }}>
            {selectedCategoryId ? (
              <>
                <b>{selectedCategory?.title}</b> <span className="mono">(ID {selectedCategoryId})</span>
              </>
            ) : (
              "Ничего не выбрано"
            )}
          </div>

          <div className="row">
            <button className="btn ghost" onClick={() => setSelectedCategoryId(null)}>
              Снять выбор
            </button>
            <button className="btn danger" onClick={deleteSelectedCategory} disabled={!selectedCategoryId}>
              Удалить категорию
            </button>
          </div>

          <div className="hr" />

          <div className="panelTitle">{selectedCategoryId ? "Добавить подкатегорию" : "Добавить категорию"}</div>

          <div className="form">
            <div className="field">
              <label>Название</label>
              <input value={catTitle} onChange={(e) => setCatTitle(e.target.value)} placeholder="Пример: Fortnite" />
            </div>

            <div className="field">
              <label>Картинка категории (URL)</label>
              <input value={catImg} onChange={(e) => setCatImg(e.target.value)} placeholder="https://…" />
            </div>

            <button className="btn ok" onClick={createCategory}>
              Добавить
            </button>

            <div className="small">
              {selectedCategoryId ? "Подкатегория появится внутри выбранной категории." : "Категория появится в корне списка."}
            </div>
          </div>
        </div>

        <div className="catalogCol" style={{ flex: 1 }}>
          <div className="panelTitle">Товары</div>

          {!selectedCategoryId ? (
            <div className="muted" style={{ padding: 12 }}>
              Выберите категорию слева - здесь появятся товары и форма добавления.
            </div>
          ) : (
            <>
              <div className="selectedBadge" style={{ marginTop: 10 }}>
                <span className="selectedHeader">
                  <span>
                    Категория: <b>{selectedCategory?.title}</b>{" "}
                    <span className="mono">(ID {selectedCategoryId})</span>
                  </span>
                </span>
              </div>

              <div style={{ marginTop: 10, overflowX: "auto" }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Название</th>
                      <th>Цена</th>
                      <th>Добавлен</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it) => (
                      <tr key={it.id}>
                        <td style={{ fontWeight: 800 }}>{it.title || "—"}</td>
                        <td className="mono">{money(it.price)}</td>
                        <td className="mono">{fmtDate(it.created_at)}</td>
                        <td>
                          <button className="btn danger" onClick={() => deleteItem(it.id)}>
                            Удалить
                          </button>
                        </td>
                      </tr>
                    ))}

                    {!items.length ? (
                      <tr>
                        <td colSpan={4} className="muted" style={{ padding: 14 }}>
                          В этой категории пока нет товаров
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>

              <div className="hr" />

              <div className="panelTitle">Добавить товар</div>

              <div className="form">
                <div className="row">
                  <div className="field" style={{ flex: 2, minWidth: 260 }}>
                    <label>Название</label>
                    <input
                      value={itemTitle}
                      onChange={(e) => setItemTitle(e.target.value)}
                      placeholder="Пример: Fortnite Crew"
                    />
                  </div>

                  <div className="field" style={{ maxWidth: 200, minWidth: 180 }}>
                    <label>Цена</label>
                    <input
                      value={itemPrice}
                      onChange={(e) => setItemPrice(e.target.value.replace(/[^\d]/g, ""))}
                      placeholder="Пример: 500"
                    />
                  </div>
                </div>

                <div className="field">
                  <label>Описание (обязательно)</label>
                  <textarea
                    value={itemDesc}
                    onChange={(e) => setItemDesc(e.target.value)}
                    placeholder="Описание товара…"
                  />
                </div>

                <div className="field">
                  <label>Картинка товара (URL)</label>
                  <input value={itemImg} onChange={(e) => setItemImg(e.target.value)} placeholder="https://…" />
                </div>

                <button className="btn ok" onClick={createItem}>
                  Добавить товар
                </button>

                <div className="small">Товар добавится в выбранную категорию.</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
