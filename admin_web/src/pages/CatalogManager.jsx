import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import S3ImagePickerField from "../components/S3ImagePickerField.jsx";
import FancySelect from "../components/FancySelect.jsx";

function fmtDate(v) {
  if (!v) return "-";
  try {
    return new Date(v).toLocaleString();
  } catch {
    return "-";
  }
}

function money(v) {
  const n = Number(v);
  if (Number.isNaN(n)) return String(v ?? "-");
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

function ImageField({ entity, shopId, value, onChange, notify, label, placeholder }) {
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  async function loadLibrary() {
    if (!shopId) {
      setLibrary([]);
      return;
    }

    setLoading(true);
    try {
      const rows = await api(`/api/catalog/media?shop_id=${encodeURIComponent(shopId)}&entity=${entity}`);
      setLibrary(Array.isArray(rows) ? rows : []);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLibrary();
  }, [shopId, entity]);

  async function uploadImage(file) {
    if (!shopId || !file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      const data = await apiForm(`/api/catalog/media/upload?shop_id=${encodeURIComponent(shopId)}&entity=${entity}`, {
        method: "POST",
        formData,
      });
      onChange(data.url || "");
      notify?.("Готово", "Картинка загружена в S3");
      await loadLibrary();
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="field">
      <label>{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />

      {value ? (
        <div className="mediaPreviewWrap">
          <img className="mediaPreview" src={value} alt="preview" />
        </div>
      ) : null}

      <div className="row">
        <label className="btn ghost mediaUploadBtn">
          {uploading ? "Загружаю..." : "Загрузить в S3"}
          <input
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            disabled={!shopId || uploading}
            onChange={(e) => uploadImage(e.target.files?.[0])}
          />
        </label>

        <button className="btn ghost" type="button" onClick={loadLibrary} disabled={!shopId || loading}>
          {loading ? "Обновляю..." : "Обновить список"}
        </button>
      </div>

      <select value={value || ""} onChange={(e) => onChange(e.target.value)} disabled={!library.length}>
        <option value="">Выбрать из S3...</option>
        {library.map((x) => (
          <option key={x.key} value={x.url}>
            {x.key}
          </option>
        ))}
      </select>

      <div className="small">Можно вставить URL вручную, загрузить файл в S3 или выбрать уже загруженный.</div>
    </div>
  );
}

function CategoryDrilldown({
  title,
  selectedId,
  onSelect,
  nodesById,
  childrenByParent,
  isParentLoaded,
  loadCategories,
  allowRoot = false,
  rootLabel = "Корень",
  excludeId = null,
}) {
  const [trail, setTrail] = useState([]);

  const currentParentId = trail.length ? trail[trail.length - 1] : null;
  const currentChildren = childrenByParent.get(currentParentId == null ? "root" : String(currentParentId)) || [];

  useEffect(() => {
    if (!isParentLoaded(currentParentId)) {
      loadCategories(currentParentId);
    }
  }, [currentParentId]);

  function pathLabel() {
    if (!trail.length) return rootLabel;
    return [rootLabel]
      .concat(trail.map((id) => nodesById.get(Number(id))?.title || `ID ${id}`))
      .join(" / ");
  }

  async function goInside(id) {
    if (!isParentLoaded(id)) await loadCategories(id);
    setTrail((prev) => [...prev, Number(id)]);
  }

  function goUp() {
    setTrail((prev) => prev.slice(0, -1));
  }

  return (
    <div className="drilldown">
      <div className="small" style={{ marginBottom: 8 }}>{title}</div>

      <div className="row" style={{ marginBottom: 8 }}>
        <span className="chip">{pathLabel()}</span>
        <button className="btn ghost" type="button" onClick={goUp} disabled={!trail.length}>
          Назад
        </button>
      </div>

      {allowRoot ? (
        <button className="btn" type="button" style={{ marginBottom: 8 }} onClick={() => onSelect("")}>
          Выбрать: {rootLabel}
        </button>
      ) : null}

      <div className="catBox" style={{ maxHeight: 220, overflowY: "auto" }}>
        {!currentChildren.length ? <div className="hint" style={{ padding: 12 }}>Нет вложенных категорий</div> : null}

        {currentChildren
          .filter((id) => Number(id) !== Number(excludeId))
          .map((id) => {
            const node = nodesById.get(Number(id));
            if (!node) return null;

            return (
              <div key={id} className="catRow" style={{ padding: 8, display: "grid", gridTemplateColumns: "1fr auto auto", gap: 8 }}>
                <div>
                  <div style={{ fontWeight: 700 }}>{node.title}</div>
                  <div className="mono">ID {node.id}</div>
                </div>

                <button className="btn ghost" type="button" onClick={() => goInside(id)}>
                  Открыть
                </button>

                <button className={`btn ${String(selectedId) === String(id) ? "ok" : ""}`} type="button" onClick={() => onSelect(String(id))}>
                  Выбрать
                </button>
              </div>
            );
          })}
      </div>
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
  const [createCatParentId, setCreateCatParentId] = useState("");

  const [editCatTitle, setEditCatTitle] = useState("");
  const [editCatImg, setEditCatImg] = useState("");
  const [editCatParentId, setEditCatParentId] = useState("");

  const [itemTitle, setItemTitle] = useState("");
  const [itemPrice, setItemPrice] = useState("");
  const [itemDesc, setItemDesc] = useState("");
  const [itemImg, setItemImg] = useState("");
  const [itemCategoryId, setItemCategoryId] = useState("");

  const [editingItemId, setEditingItemId] = useState(null);
  const [editItemTitle, setEditItemTitle] = useState("");
  const [editItemPrice, setEditItemPrice] = useState("");
  const [editItemDesc, setEditItemDesc] = useState("");
  const [editItemImg, setEditItemImg] = useState("");
  const [editItemCategoryId, setEditItemCategoryId] = useState("");

  const [treeLoading, setTreeLoading] = useState(false);
  const [savingCategory, setSavingCategory] = useState(false);
  const [savingItem, setSavingItem] = useState(false);

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

  function resetItemForm() {
    setItemTitle("");
    setItemPrice("");
    setItemDesc("");
    setItemImg("");
    setItemCategoryId(selectedCategoryId ? String(selectedCategoryId) : "");
  }

  function resetEditingItem() {
    setEditingItemId(null);
    setEditItemTitle("");
    setEditItemPrice("");
    setEditItemDesc("");
    setEditItemImg("");
    setEditItemCategoryId("");
  }

  function syncCategoryEditor(node) {
    if (!node) {
      setEditCatTitle("");
      setEditCatImg("");
      setEditCatParentId("");
      return;
    }
    setEditCatTitle(node.title || "");
    setEditCatImg(node.img || "");
    setEditCatParentId(node.parent_id == null ? "" : String(node.parent_id));
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
    setCreateCatParentId("");
    syncCategoryEditor(null);
    resetEditingItem();

    loadCategories(null);
  }, [shopId]);

  useEffect(() => {
    loadItems();
    resetEditingItem();
  }, [shopId, selectedCategoryId]);

  useEffect(() => {
    syncCategoryEditor(selectedCategory);
    if (selectedCategoryId) setItemCategoryId(String(selectedCategoryId));
  }, [selectedCategoryId, selectedCategory]);

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

  async function createCategory() {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    if (!catTitle.trim()) return notify?.("Ошибка", "Введите название категории");
    if (!catImg.trim()) return notify?.("Ошибка", "Добавьте картинку категории");

    const parentId = createCatParentId ? Number(createCatParentId) : null;

    try {
      await api("/api/catalog/categories", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          title: catTitle.trim(),
          img: catImg.trim(),
          parent_id: parentId,
        },
      });

      setCatTitle("");
      setCatImg("");
      notify?.("Готово", parentId ? "Подкатегория создана" : "Категория создана");

      await loadCategories(parentId);
      if (parentId) setOpenIds((prev) => new Set(prev).add(parentId));
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function updateSelectedCategory() {
    if (!shopId || !selectedCategoryId) return;
    if (!editCatTitle.trim()) return notify?.("Ошибка", "Введите название категории");
    if (!editCatImg.trim()) return notify?.("Ошибка", "Добавьте картинку категории");

    setSavingCategory(true);
    try {
      const p = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/categories/${Number(selectedCategoryId)}?${p.toString()}`, {
        method: "PATCH",
        body: {
          title: editCatTitle.trim(),
          img: editCatImg.trim(),
          parent_id: editCatParentId ? Number(editCatParentId) : null,
        },
      });

      notify?.("Готово", "Категория обновлена");
      await loadCategories(null);
      if (selectedCategory?.parent_id != null) await loadCategories(Number(selectedCategory.parent_id));
      if (selectedCategoryId) await loadCategories(Number(selectedCategoryId));
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setSavingCategory(false);
    }
  }

  async function deleteSelectedCategory() {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    if (!selectedCategoryId) return notify?.("Ошибка", "Выберите категорию слева");

    const ok = window.confirm("Удалить категорию? В ней не должно быть товаров и подкатегорий.");
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
    if (!itemCategoryId) return notify?.("Ошибка", "Выберите категорию для товара");
    if (!itemTitle.trim()) return notify?.("Ошибка", "Введите название товара");
    if (!itemImg.trim()) return notify?.("Ошибка", "Добавьте картинку товара");

    const price = Number(String(itemPrice).replace(/[^\d]/g, ""));
    if (Number.isNaN(price)) return notify?.("Ошибка", "Введите цену");

    try {
      await api("/api/catalog/items", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          category_id: Number(itemCategoryId),
          title: itemTitle.trim(),
          price,
          description: itemDesc?.trim() ? itemDesc.trim() : null,
          img: itemImg.trim(),
        },
      });

      resetItemForm();
      notify?.("Готово", "Товар добавлен");
      await loadItems();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  function startEditItem(it) {
    setEditingItemId(Number(it.id));
    setEditItemTitle(it.title || "");
    setEditItemPrice(String(it.price ?? ""));
    setEditItemDesc(it.description || "");
    setEditItemImg(it.img || "");
    setEditItemCategoryId(String(it.category_id || selectedCategoryId || ""));
  }

  async function saveItem() {
    if (!shopId || !editingItemId) return;
    if (!editItemTitle.trim()) return notify?.("Ошибка", "Введите название товара");
    if (!editItemImg.trim()) return notify?.("Ошибка", "Добавьте изображение товара");

    const price = Number(String(editItemPrice).replace(/[^\d]/g, ""));
    if (Number.isNaN(price)) return notify?.("Ошибка", "Введите корректную цену");
    if (!editItemCategoryId) return notify?.("Ошибка", "Выберите категорию");

    setSavingItem(true);
    try {
      const p = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/items/${Number(editingItemId)}?${p.toString()}`, {
        method: "PATCH",
        body: {
          title: editItemTitle.trim(),
          price,
          description: editItemDesc.trim() ? editItemDesc.trim() : null,
          img: editItemImg.trim(),
          category_id: Number(editItemCategoryId),
        },
      });

      notify?.("Готово", "Товар обновлен");
      resetEditingItem();
      await loadItems();
      await loadCategories(null);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setSavingItem(false);
    }
  }

  async function deleteItem(itemId) {
    if (!shopId) return notify?.("Ошибка", "Сначала выберите магазин");
    const ok = window.confirm("Удалить этот товар?");
    if (!ok) return;

    try {
      const p = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/items/${Number(itemId)}?${p.toString()}`, { method: "DELETE" });
      notify?.("Готово", "Товар удален");
      if (Number(editingItemId) === Number(itemId)) resetEditingItem();
      await loadItems();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

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

  return (
    <div className="card catalogCard">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "end" }}>
        <div>
          <h2 style={{ margin: 0 }}>Каталог магазина</h2>
          <div className="hint" style={{ marginTop: 6 }}>
            {shopTitle ? (
              <>
                Активный магазин: <b>{shopTitle}</b>
              </>
            ) : (
              "Выберите магазин, чтобы управлять категориями и товарами"
            )}
          </div>
        </div>

        <div className="field" style={{ minWidth: 320 }}>
          <label>Магазин</label>
          <FancySelect
            value={shopId}
            onChange={setShopId}
            options={shops.map((s) => ({ value: String(s.id), label: s.title }))}
            placeholder="Выберите магазин"
          />
        </div>
      </div>

      <div className="hr" />

      <div className="catalogGrid">
        <div className="catalogCol">
          <div className="panelTitle">Категории</div>

          <div className="row" style={{ marginBottom: 10 }}>
            <button className="btn ghost" onClick={expandAll} disabled={!shopId || treeLoading}>
              {treeLoading ? "Загружаю..." : "Развернуть все"}
            </button>
            <button className="btn ghost" onClick={collapseAll} disabled={!shopId || treeLoading}>
              Свернуть все
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

            {!flatTree.length ? <div className="hint" style={{ padding: 12 }}>Пока нет категорий</div> : null}
          </div>

          <div className="hr" />

          <div className="panelTitle">Создать категорию</div>

          <div className="form">
            <div className="field">
              <label>Название</label>
              <input value={catTitle} onChange={(e) => setCatTitle(e.target.value)} placeholder="Например: Fortnite" />
            </div>

            <CategoryDrilldown
              title="Проваливание: выбор родительской категории"
              selectedId={createCatParentId}
              onSelect={setCreateCatParentId}
              nodesById={nodesById}
              childrenByParent={childrenByParent}
              isParentLoaded={isParentLoaded}
              loadCategories={loadCategories}
              allowRoot
              rootLabel="Корень каталога"
            />

            <S3ImagePickerField
              entity="categories"
              shopId={shopId}
              value={catImg}
              onChange={setCatImg}
              notify={notify}
              label="Картинка категории"
              placeholder="https://..."
            />

            <button className="btn ok" onClick={createCategory}>Добавить категорию</button>
          </div>
        </div>

        <div className="catalogCol" style={{ flex: 1 }}>
          <div className="panelTitle">Управление выбранной категорией</div>

          {!selectedCategoryId ? (
            <div className="hint" style={{ padding: 12 }}>
              Выберите категорию слева, чтобы редактировать ее и управлять товарами.
            </div>
          ) : (
            <>
              <div className="selectedBadge" style={{ marginTop: 10 }}>
                <div className="selectedHeader">
                  <span>
                    Категория: <b>{selectedCategory?.title}</b> <span className="mono">(ID {selectedCategoryId})</span>
                  </span>
                </div>
              </div>

              <div className="form" style={{ marginTop: 12 }}>
                <div className="field" style={{ flex: 1 }}>
                  <label>Название категории</label>
                  <input value={editCatTitle} onChange={(e) => setEditCatTitle(e.target.value)} />
                </div>

                <CategoryDrilldown
                  title="Проваливание: изменить родителя категории"
                  selectedId={editCatParentId}
                  onSelect={setEditCatParentId}
                  nodesById={nodesById}
                  childrenByParent={childrenByParent}
                  isParentLoaded={isParentLoaded}
                  loadCategories={loadCategories}
                  allowRoot
                  rootLabel="Корень каталога"
                  excludeId={selectedCategoryId}
                />

            <S3ImagePickerField
                  entity="categories"
                  shopId={shopId}
                  value={editCatImg}
                  onChange={setEditCatImg}
                  notify={notify}
                  label="Картинка категории"
                  placeholder="https://..."
                />

                <div className="row">
                  <button className="btn ok" onClick={updateSelectedCategory} disabled={savingCategory}>
                    {savingCategory ? "Сохраняю..." : "Сохранить категорию"}
                  </button>
                  <button className="btn danger" onClick={deleteSelectedCategory}>Удалить категорию</button>
                  <button className="btn ghost" onClick={() => setSelectedCategoryId(null)}>Снять выбор</button>
                </div>
              </div>

              <div className="hr" />

              <div className="panelTitle">Товары</div>

              <div style={{ marginTop: 10, overflowX: "auto" }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Название</th>
                      <th>Цена</th>
                      <th>Добавлен</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it) => (
                      <tr key={it.id}>
                        <td className="mono">{it.id}</td>
                        <td style={{ fontWeight: 700 }}>{it.title || "-"}</td>
                        <td className="mono">{money(it.price)}</td>
                        <td className="mono">{fmtDate(it.created_at)}</td>
                        <td>
                          <div className="row" style={{ justifyContent: "flex-end" }}>
                            <button className="btn" onClick={() => startEditItem(it)}>Изменить</button>
                            <button className="btn danger" onClick={() => deleteItem(it.id)}>Удалить</button>
                          </div>
                        </td>
                      </tr>
                    ))}

                    {!items.length ? (
                      <tr>
                        <td colSpan={5} className="hint" style={{ padding: 14 }}>
                          В этой категории пока нет товаров
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>

              <div className="hr" />

              <div className="grid cols2">
                <div className="subCard">
                  <div className="panelTitle">Добавить товар</div>
                  <div className="form" style={{ marginTop: 10 }}>
                    <div className="field">
                      <label>Название</label>
                      <input value={itemTitle} onChange={(e) => setItemTitle(e.target.value)} placeholder="Например: Fortnite Crew" />
                    </div>

                    <div className="field">
                      <label>Цена</label>
                      <input value={itemPrice} onChange={(e) => setItemPrice(e.target.value.replace(/[^\d]/g, ""))} placeholder="500" />
                    </div>

                    <div className="field">
                      <label>Описание</label>
                      <textarea value={itemDesc} onChange={(e) => setItemDesc(e.target.value)} placeholder="Описание товара" />
                    </div>

                    <CategoryDrilldown
                      title="Проваливание: выбрать категорию товара"
                      selectedId={itemCategoryId}
                      onSelect={setItemCategoryId}
                      nodesById={nodesById}
                      childrenByParent={childrenByParent}
                      isParentLoaded={isParentLoaded}
                      loadCategories={loadCategories}
                    />

                    <S3ImagePickerField
                      entity="items"
                      shopId={shopId}
                      value={itemImg}
                      onChange={setItemImg}
                      notify={notify}
                      label="Картинка товара"
                      placeholder="https://..."
                    />

                    <button className="btn ok" onClick={createItem}>Добавить товар</button>
                  </div>
                </div>

                <div className="subCard">
                  <div className="panelTitle">Редактировать товар</div>
                  {!editingItemId ? (
                    <div className="hint" style={{ marginTop: 10 }}>Нажмите "Изменить" рядом с нужным товаром.</div>
                  ) : (
                    <div className="form" style={{ marginTop: 10 }}>
                      <div className="field">
                        <label>Название</label>
                        <input value={editItemTitle} onChange={(e) => setEditItemTitle(e.target.value)} />
                      </div>

                      <div className="field" style={{ flex: 1 }}>
                        <label>Цена</label>
                        <input value={editItemPrice} onChange={(e) => setEditItemPrice(e.target.value.replace(/[^\d]/g, ""))} />
                      </div>

                      <div className="field">
                        <label>Описание</label>
                        <textarea value={editItemDesc} onChange={(e) => setEditItemDesc(e.target.value)} />
                      </div>

                      <CategoryDrilldown
                        title="Проваливание: изменить категорию товара"
                        selectedId={editItemCategoryId}
                        onSelect={setEditItemCategoryId}
                        nodesById={nodesById}
                        childrenByParent={childrenByParent}
                        isParentLoaded={isParentLoaded}
                        loadCategories={loadCategories}
                      />

                      <S3ImagePickerField
                        entity="items"
                        shopId={shopId}
                        value={editItemImg}
                        onChange={setEditItemImg}
                        notify={notify}
                        label="Картинка"
                        placeholder="https://..."
                      />

                      <div className="row">
                        <button className="btn ok" onClick={saveItem} disabled={savingItem}>
                          {savingItem ? "Сохраняю..." : "Сохранить товар"}
                        </button>
                        <button className="btn ghost" onClick={resetEditingItem}>Отменить</button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}


