import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.rows)) return data.rows;
  return [];
}

function keyOf(parentId) {
  return parentId == null ? "root" : String(parentId);
}

export default function CategoryDrilldownPicker({
  shopId,
  value,
  onChange,
  notify,
  title = "Выбор категории",
  rootLabel = "Корень",
  allowRoot = false,
  excludeId = null,
}) {
  const [nodesById, setNodesById] = useState(new Map());
  const [childrenByParent, setChildrenByParent] = useState(new Map());
  const [loadedParents, setLoadedParents] = useState(new Set());
  const [trail, setTrail] = useState([]);
  const [loading, setLoading] = useState(false);

  const currentParentId = trail.length ? trail[trail.length - 1] : null;
  const currentChildren = childrenByParent.get(keyOf(currentParentId)) || [];

  function isLoaded(parentId) {
    return loadedParents.has(keyOf(parentId));
  }

  async function loadLevel(parentId) {
    if (!shopId) return [];
    if (isLoaded(parentId)) return [];

    setLoading(true);
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      if (parentId != null) qs.set("parent_id", String(parentId));
      const data = await api(`/api/catalog/categories?${qs.toString()}`);
      const rows = normalizeList(data);

      setNodesById((prev) => {
        const next = new Map(prev);
        for (const row of rows) next.set(Number(row.id), row);
        return next;
      });
      setChildrenByParent((prev) => {
        const next = new Map(prev);
        next.set(keyOf(parentId), rows.map((x) => Number(x.id)));
        return next;
      });
      setLoadedParents((prev) => {
        const next = new Set(prev);
        next.add(keyOf(parentId));
        return next;
      });
      return rows;
    } catch (e) {
      notify?.("Ошибка", e.message);
      return [];
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setNodesById(new Map());
    setChildrenByParent(new Map());
    setLoadedParents(new Set());
    setTrail([]);
  }, [shopId]);

  useEffect(() => {
    if (!shopId) return;
    loadLevel(currentParentId);
  }, [shopId, currentParentId]);

  const pathText = useMemo(() => {
    if (!trail.length) return rootLabel;
    return [rootLabel]
      .concat(trail.map((id) => nodesById.get(Number(id))?.title || `ID ${id}`))
      .join(" / ");
  }, [trail, nodesById, rootLabel]);

  async function openNode(id) {
    await loadLevel(id);
    setTrail((prev) => [...prev, Number(id)]);
  }

  function goBack() {
    setTrail((prev) => prev.slice(0, -1));
  }

  return (
    <div className="drilldown">
      <div className="small" style={{ marginBottom: 8 }}>{title}</div>

      <div className="row" style={{ marginBottom: 8 }}>
        <span className="chip">{pathText}</span>
        <button className="btn ghost" type="button" onClick={goBack} disabled={!trail.length}>
          Назад
        </button>
      </div>

      {allowRoot ? (
        <button className={`btn ${String(value) === "" ? "ok" : ""}`} type="button" style={{ marginBottom: 8 }} onClick={() => onChange("")}>
          Выбрать: {rootLabel}
        </button>
      ) : null}

      <div className="catBox" style={{ maxHeight: 220, overflowY: "auto" }}>
        {!currentChildren.length ? (
          <div className="hint" style={{ padding: 12 }}>
            {loading ? "Загрузка..." : "Нет вложенных категорий"}
          </div>
        ) : null}

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

                <button className="btn ghost" type="button" onClick={() => openNode(id)}>
                  Открыть
                </button>

                <button
                  className={`btn ${String(value) === String(id) ? "ok" : ""}`}
                  type="button"
                  onClick={() => onChange(String(id))}
                >
                  Выбрать
                </button>
              </div>
            );
          })}
      </div>
    </div>
  );
}
