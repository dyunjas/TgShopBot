import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import CategoryDrilldownPicker from "../components/CategoryDrilldownPicker.jsx";
import S3ImagePickerField from "../components/S3ImagePickerField.jsx";
import ShopSelect from "../components/ShopSelect.jsx";

export default function Items({ notify }) {
  const [shopId, setShopId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [items, setItems] = useState([]);

  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("0");
  const [desc, setDesc] = useState("");
  const [img, setImg] = useState("");
  const [createCategoryId, setCreateCategoryId] = useState("");

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
          category_id: Number(createCategoryId),
          title,
          price: Number(price),
          description: desc || null,
          img,
        },
      });
      setTitle("");
      setPrice("0");
      setDesc("");
      setImg("");
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

  useEffect(() => {
    load();
  }, [shopId, categoryId]);

  useEffect(() => {
    setCreateCategoryId("");
  }, [shopId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Товары</h2>

        <div className="row">
          <ShopSelect value={shopId} onChange={setShopId} notify={notify} label="Магазин" />
          <div className="field">
            <label>category_id (фильтр)</label>
            <input value={categoryId} onChange={(e) => setCategoryId(e.target.value.replace(/[^\d]/g, ""))} placeholder="10" />
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
          <div className="small">Нужны: shop_id + категория (через проваливание).</div>

          <div className="field">
            <label>title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="VPN 1 мес" />
          </div>

          <CategoryDrilldownPicker
            shopId={shopId}
            value={createCategoryId}
            onChange={setCreateCategoryId}
            notify={notify}
            title="Проваливание: выбор категории товара"
          />

          <S3ImagePickerField
            shopId={shopId}
            entity="items"
            value={img}
            onChange={setImg}
            notify={notify}
            label="img (S3 / url)"
            placeholder="https://..."
          />

          <div className="row">
            <div className="field">
              <label>price</label>
              <input value={price} onChange={(e) => setPrice(e.target.value.replace(/[^\d]/g, ""))} />
            </div>
          </div>

          <div className="field">
            <label>description</label>
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Описание..." />
          </div>

          <button className="btn ok" onClick={create} disabled={!shopId || !createCategoryId || !title || !img}>
            Создать
          </button>
        </div>
      </div>
    </div>
  );
}
