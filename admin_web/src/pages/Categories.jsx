import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Categories({ notify }) {
  const [shopId, setShopId] = useState("");
  const [parentId, setParentId] = useState("");
  const [cats, setCats] = useState([]);

  const [title, setTitle] = useState("");
  const [img, setImg] = useState("");

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
        body: { shop_id: Number(shopId), title, img, parent_id: parentId ? Number(parentId) : null }
      });
      setTitle(""); setImg("");
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

  useEffect(() => { load(); }, [shopId, parentId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Категории</h2>

        <div className="row">
          <div className="field">
            <label>shop_id</label>
            <input value={shopId} onChange={(e) => setShopId(e.target.value.replace(/[^\d]/g,""))} placeholder="1" />
          </div>
          <div className="field">
            <label>parent_id (опционально)</label>
            <input value={parentId} onChange={(e) => setParentId(e.target.value.replace(/[^\d]/g,""))} placeholder="" />
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
          <div className="small">Нужны: shop_id, title, img (file_id/URL), parent_id по желанию.</div>
          <div className="field">
            <label>title</label>
            <input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="VPN" />
          </div>
          <div className="field">
            <label>img (telegram file_id / url)</label>
            <input value={img} onChange={(e)=>setImg(e.target.value)} placeholder="AgACAg..." />
          </div>
          <button className="btn ok" onClick={create} disabled={!shopId || !title || !img}>Создать</button>
        </div>
      </div>
    </div>
  );
}
