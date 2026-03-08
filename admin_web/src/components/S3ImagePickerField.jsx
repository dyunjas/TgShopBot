import React, { useEffect, useState } from "react";
import { api, apiForm } from "../api.js";

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.rows)) return data.rows;
  return [];
}

export default function S3ImagePickerField({
  shopId,
  entity,
  value,
  onChange,
  notify,
  label = "Картинка",
  placeholder = "https://...",
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [items, setItems] = useState([]);
  const [fileInputKey, setFileInputKey] = useState(0);

  async function loadMedia() {
    if (!shopId) {
      setItems([]);
      return;
    }
    setLoading(true);
    try {
      const rows = await api(`/api/catalog/media?shop_id=${encodeURIComponent(shopId)}&entity=${entity}`);
      setItems(normalizeList(rows));
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  async function onUpload(file) {
    if (!shopId || !file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const data = await apiForm(`/api/catalog/media/upload?shop_id=${encodeURIComponent(shopId)}&entity=${entity}`, {
        method: "POST",
        formData: fd,
      });
      const url = data?.url || "";
      onChange(url);
      await loadMedia();
      notify?.("Готово", "Картинка загружена");
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setUploading(false);
      setFileInputKey((v) => v + 1);
    }
  }

  useEffect(() => {
    if (open) loadMedia();
  }, [open, shopId, entity]);

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
        <button className="btn ghost" type="button" disabled={!shopId} onClick={() => setOpen(true)}>
          Открыть медиатеку
        </button>
      </div>

      {open ? (
        <div className="modalOverlay" onMouseDown={() => setOpen(false)}>
          <div className="modal mediaPickerModal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <div className="modalTitle">Медиатека</div>
              <button className="btn ghost sm" type="button" onClick={() => setOpen(false)}>
                Закрыть
              </button>
            </div>

            <div className="modalBody">
              <div className="row" style={{ marginBottom: 10 }}>
                <button className="btn ghost" type="button" onClick={loadMedia} disabled={loading}>
                  {loading ? "Обновляю..." : "Обновить"}
                </button>
                <label className="btn ghost mediaUploadBtn">
                  {uploading ? "Загружаю..." : "Загрузить"}
                  <input
                    key={fileInputKey}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    disabled={!shopId || uploading}
                    onChange={(e) => onUpload(e.target.files?.[0])}
                  />
                </label>
              </div>

              <div className="mediaGrid">
                {items.map((it) => (
                  <button
                    key={it.key}
                    type="button"
                    className={`mediaTile ${value === it.url ? "selected" : ""}`}
                    onClick={() => {
                      onChange(it.url);
                      setOpen(false);
                    }}
                    title={it.key}
                  >
                    <img src={it.url} alt={it.key} />
                    <span>{it.key.split("/").pop()}</span>
                  </button>
                ))}

                {!items.length ? <div className="hint">Нет файлов в S3</div> : null}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
