import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Items({ notify }) {
  const [shopId, setShopId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [items, setItems] = useState([]);

  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("0");
  const [desc, setDesc] = useState("");
  const [img, setImg] = useState("");

  async function load() {
    if (!shopId) return;
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      if (categoryId) qs.set("category_id", String(categoryId));
      const data = await api(`/api/catalog/items?${qs.toString()}`);
      setItems(data);
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function create() {
    try {
      await api("/api/catalog/items", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          category_id: Number(categoryId),
          title,
          price: Number(price),
          description: desc || null,
          img
        }
      });
      setTitle(""); setPrice("0"); setDesc(""); setImg("");
      notify("Ок", "Товар создан");
      load();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function del(id) {
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/catalog/items/${id}?${qs.toString()}`, { method: "DELETE" });
      notify("Ок", "Товар удалён");
      load();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  useEffect(() => { load(); }, [shopId, categoryId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Товары</h2>

        <div className="row">
          <div className="field">
            <label>shop_id</label>
            <input value={shopId} onChange={(e)=>setShopId(e.target.value.replace(/[^\d]/g,""))} placeholder="1" />
          </div>
          <div className="field">
            <label>category_id (фильтр)</label>
            <input value={categoryId} onChange={(e)=>setCategoryId(e.target.value.replace(/[^\d]/g,""))} placeholder="10" />
          </div>
        </div>

        <button className="btn" onClick={load} disabled={!shopId}>Загрузить</button>

        <div className="hr" />

        <table className="table">
          <thead>
            <tr><th>ID</th><th>Title</th><th>Price</th><th>Cat</th><th>Img</th><th></th></tr>
          </thead>
          <tbody>
            {items.map(i => (
              <tr key={i.id}>
                <td className="mono">{i.id}</td>
                <td>{i.title}</td>
                <td className="mono">{i.price}</td>
                <td className="mono">{i.category_id}</td>
                <td className="mono">{(i.img || "").slice(0, 18)}{i.img?.length > 18 ? "..." : ""}</td>
                <td><button className="btn danger" onClick={() => del(i.id)}>Удалить</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Создать товар</h2>
        <div className="form">
          <div className="small">Нужны: shop_id + category_id.</div>

          <div className="field">
            <label>title</label>
            <input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="VPN 1 мес" />
          </div>

          <div className="row">
            <div className="field">
              <label>price</label>
              <input value={price} onChange={(e)=>setPrice(e.target.value.replace(/[^\d]/g,""))} />
            </div>
            <div className="field">
              <label>img (telegram file_id / url)</label>
              <input value={img} onChange={(e)=>setImg(e.target.value)} placeholder="AgACAg..." />
            </div>
          </div>

          <div className="field">
            <label>description</label>
            <textarea value={desc} onChange={(e)=>setDesc(e.target.value)} placeholder="Описание..." />
          </div>

          <button className="btn ok" onClick={create} disabled={!shopId || !categoryId || !title || !img}>
            Создать
          </button>
        </div>
      </div>
    </div>
  );
}
