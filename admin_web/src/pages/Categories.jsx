import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import CategoryDrilldownPicker from "../components/CategoryDrilldownPicker.jsx";
import S3ImagePickerField from "../components/S3ImagePickerField.jsx";
import ShopSelect from "../components/ShopSelect.jsx";

export default function Categories({ notify }) {
  const [shopId, setShopId] = useState("");
  const [parentId, setParentId] = useState("");
  const [cats, setCats] = useState([]);

  const [title, setTitle] = useState("");
  const [img, setImg] = useState("");
  const [createParentId, setCreateParentId] = useState("");

  async function load() {
    if (!shopId) return;
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      if (parentId) qs.set("parent_id", String(parentId));
      const data = await api(`/api/catalog/categories?${qs.toString()}`);
      setCats(data);
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function create() {
    try {
      await api("/api/catalog/categories", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          title,
          img,
          parent_id: createParentId ? Number(createParentId) : null,
        },
      });
      setTitle("");
      setImg("");
      setCreateParentId("");
      notify("Ок", "Категория создана");
      load();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function del(id) {
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/categories/${id}?${qs.toString()}`, { method: "DELETE" });
      notify("Ок", "Категория удалена");
      load();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  useEffect(() => {
    load();
  }, [shopId, parentId]);

  useEffect(() => {
    setCreateParentId("");
  }, [shopId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Категории</h2>

        <div className="row">
          <ShopSelect value={shopId} onChange={setShopId} notify={notify} label="Магазин" />
          <div className="field">
            <label>parent_id (фильтр)</label>
            <input value={parentId} onChange={(e) => setParentId(e.target.value.replace(/[^\d]/g, ""))} placeholder="" />
          </div>
        </div>

        <button className="btn" onClick={load} disabled={!shopId}>Загрузить</button>

        <div className="hr" />

        <table className="table">
          <thead>
            <tr><th>ID</th><th>Title</th><th>Parent</th><th>Img</th><th></th></tr>
          </thead>
          <tbody>
            {cats.map(c => (
              <tr key={c.id}>
                <td className="mono">{c.id}</td>
                <td>{c.title}</td>
                <td className="mono">{c.parent_id ?? "-"}</td>
                <td className="mono">{(c.img || "").slice(0, 18)}{c.img?.length > 18 ? "..." : ""}</td>
                <td><button className="btn danger" onClick={() => del(c.id)}>Удалить</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Создать категорию</h2>
        <div className="form">
          <div className="small">Нужны: shop_id, title, img. Родителя выбирайте через проваливание.</div>

          <div className="field">
            <label>title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="VPN" />
          </div>

          <CategoryDrilldownPicker
            shopId={shopId}
            value={createParentId}
            onChange={setCreateParentId}
            notify={notify}
            title="Проваливание: выбор родительской категории"
            rootLabel="Корень каталога"
            allowRoot
          />

          <S3ImagePickerField
            shopId={shopId}
            entity="categories"
            value={img}
            onChange={setImg}
            notify={notify}
            label="img (S3 / url)"
            placeholder="https://..."
          />

          <button className="btn ok" onClick={create} disabled={!shopId || !title || !img}>Создать</button>
        </div>
      </div>
    </div>
  );
}
