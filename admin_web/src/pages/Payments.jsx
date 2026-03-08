import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import ShopSelect from "../components/ShopSelect.jsx";
import FancySelect from "../components/FancySelect.jsx";

const PROVIDER_LABEL = {
  lava: "Lava",
  pally: "Pally",
};

function maskSecret(v) {
  if (!v) return "-";
  const s = String(v);
  if (s.length <= 6) return "••••••";
  return `${s.slice(0, 2)}••••••${s.slice(-2)}`;
}

export default function Payments({ notify }) {
  const [shopId, setShopId] = useState("");
  const [cfgs, setCfgs] = useState([]);
  const [loading, setLoading] = useState(false);

  const [provider, setProvider] = useState("lava");
  const [shopIdValue, setShopIdValue] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [apiToken, setApiToken] = useState("");

  const [successUrl, setSuccessUrl] = useState("");
  const [failUrl, setFailUrl] = useState("");

  const [isActive, setIsActive] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const helpText = useMemo(() => {
    if (provider === "lava") return "Для Lava обычно нужны: ID магазина и секретный ключ.";
    if (provider === "pally") return "Для Pally обязательны: shop_id_value и api_token.";
    return "";
  }, [provider]);

  async function load() {
    if (!shopId) return;
    setLoading(true);
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      const data = await api(`/api/payments?${qs.toString()}`);
      setCfgs(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setSelectedId(null);
    setProvider("lava");
    setShopIdValue("");
    setSecretKey("");
    setApiToken("");
    setSuccessUrl("");
    setFailUrl("");
    setIsActive(true);
  }

  function fillFormFromCfg(c) {
    setSelectedId(c.id);
    setProvider(c.provider || "lava");
    setShopIdValue(c.shop_id_value || "");
    setSecretKey(c.secret_key || "");
    setApiToken(c.api_token || "");
    setSuccessUrl(c.success_url || "");
    setFailUrl(c.fail_url || "");
    setIsActive(!!c.is_active);
  }

  async function create() {
    if (!shopId) return notify?.("Ошибка", "Выберите магазин");
    if (provider === "pally" && (!shopIdValue.trim() || !apiToken.trim())) {
      return notify?.("Ошибка", "Для Pally обязательны shop_id_value и api_token");
    }
    try {
      await api("/api/payments", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          provider,
          shop_id_value: shopIdValue || null,
          secret_key: secretKey || null,
          api_token: apiToken || null,

          success_url: successUrl || "",
          fail_url: failUrl || "",

          is_active: isActive,
        },
      });
      notify?.("Ок", "Платежка добавлена");
      resetForm();
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function updateSelected() {
    if (!shopId) return notify?.("Ошибка", "Выберите магазин");
    if (!selectedId) return notify?.("Ошибка", "Выберите конфиг из списка слева");
    if (provider === "pally" && (!shopIdValue.trim() || !apiToken.trim())) {
      return notify?.("Ошибка", "Для Pally обязательны shop_id_value и api_token");
    }
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/payments/${selectedId}?${qs.toString()}`, {
        method: "PATCH",
        body: {
          shop_id_value: shopIdValue || null,
          secret_key: secretKey || null,
          api_token: apiToken || null,

          success_url: successUrl || "",
          fail_url: failUrl || "",

          is_active: isActive,
        },
      });
      notify?.("Ок", "Изменения сохранены");
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function del(cfgId) {
    if (!shopId) return notify?.("Ошибка", "Выберите магазин");
    const ok = window.confirm("Удалить эту платежку?");
    if (!ok) return;

    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/payments/${cfgId}?${qs.toString()}`, { method: "DELETE" });

      notify?.("Ок", "Платежка удалена");

      if (selectedId === cfgId) resetForm();
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  useEffect(() => {
    load();
  }, [shopId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Платежные системы</h2>
        <div className="muted" style={{ marginTop: 6 }}>
          {loading ? "Загружаю..." : "Подключения оплаты для выбранного магазина"}
        </div>

        <div className="row controlRow" style={{ marginTop: 12 }}>
          <ShopSelect value={shopId} onChange={setShopId} notify={notify} label="Магазин" showRefresh={false} />

          <div className="field">
            <label>Провайдер</label>
            <FancySelect
              value={provider}
              onChange={setProvider}
              options={[
                { value: "lava", label: PROVIDER_LABEL.lava },
                { value: "pally", label: PROVIDER_LABEL.pally },
              ]}
            />
          </div>
        </div>

        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn" onClick={load} disabled={!shopId || loading}>
            Обновить список
          </button>

          <button className="btn ghost" onClick={resetForm} disabled={!shopId || loading}>
            Сбросить форму
          </button>

          {selectedId ? (
            <div className="muted" style={{ marginLeft: "auto", alignSelf: "center" }}>
              Выбрано: <b>#{selectedId}</b>
            </div>
          ) : null}
        </div>

        <div className="hr" />

        <table className="table">
          <thead>
            <tr>
              <th>Подключение</th>
              <th>Состояние</th>
              <th style={{ width: 220 }} />
            </tr>
          </thead>
          <tbody>
            {!loading && cfgs.length === 0 && (
              <tr>
                <td colSpan={3} className="muted" style={{ padding: 16 }}>
                  Пока ничего не подключено
                </td>
              </tr>
            )}

            {cfgs.map((c) => (
              <tr key={c.id}>
                <td>
                  <div style={{ fontWeight: 900 }}>
                    {PROVIDER_LABEL[c.provider] || c.provider || "Платежка"}
                  </div>

                  <div className="small">
                    {c.provider === "lava" ? (
                      <>
                        ID: <span className="mono">{c.shop_id_value || "-"}</span> · ключ: <span className="mono">{maskSecret(c.secret_key)}</span>
                      </>
                    ) : (
                      <>
                        токен: <span className="mono">{maskSecret(c.api_token)}</span>
                      </>
                    )}
                  </div>

                  <div className="small">
                    success_url: <span className="mono">{c.success_url || "-"}</span>
                  </div>
                  <div className="small">
                    fail_url: <span className="mono">{c.fail_url || "-"}</span>
                  </div>
                </td>

                <td>
                  <span className={`statusPill ${c.is_active ? "on" : "off"}`}>
                    {c.is_active ? "Активна" : "Выключена"}
                  </span>
                </td>

                <td className="row" style={{ gap: 8 }}>
                  <button className="btn ghost" onClick={() => fillFormFromCfg(c)}>
                    Редактировать
                  </button>
                  <button className="btn danger" onClick={() => del(c.id)}>
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="small" style={{ marginTop: 10 }}>
          Подсказка: {helpText}
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{selectedId ? "Редактирование платежки" : "Подключить платежку"}</h2>
        <div className="muted" style={{ marginTop: 6 }}>
          {selectedId ? "Измените поля и сохраните" : "Заполните данные и создайте подключение"}
        </div>

        <div className="hr" />

        <div className="form">
          {provider === "lava" ? (
            <>
              <div className="field">
                <label>ID магазина в Lava</label>
                <input
                  value={shopIdValue}
                  onChange={(e) => setShopIdValue(e.target.value)}
                  placeholder="Пример: 12345"
                />
              </div>

              <div className="field">
                <label>Секретный ключ</label>
                <input
                  value={secretKey}
                  onChange={(e) => setSecretKey(e.target.value)}
                  placeholder="Введите секретный ключ"
                />
              </div>
            </>
          ) : (
            <>
              <div className="field">
                <label>ID магазина в Pally</label>
                <input
                  value={shopIdValue}
                  onChange={(e) => setShopIdValue(e.target.value)}
                  placeholder="Введите shop_id_value"
                />
              </div>
              <div className="field">
                <label>API-токен</label>
                <input
                  value={apiToken}
                  onChange={(e) => setApiToken(e.target.value)}
                  placeholder="Введите API-токен"
                />
              </div>
            </>
          )}

          <div className="field">
            <label>URL удачи</label>
            <input
              value={successUrl}
              onChange={(e) => setSuccessUrl(e.target.value)}
              placeholder="https://..."
            />
            <div className="small">Куда редиректить пользователя после успешной оплаты (если провайдер поддерживает).</div>
          </div>

          <div className="field">
            <label>URL неудачи</label>
            <input
              value={failUrl}
              onChange={(e) => setFailUrl(e.target.value)}
              placeholder="https://..."
            />
            <div className="small">Куда редиректить пользователя при ошибке/отмене оплаты.</div>
          </div>

          <div className="row" style={{ alignItems: "center" }}>
            <button className={`btn ${isActive ? "ok" : "ghost"}`} onClick={() => setIsActive(!isActive)}>
              {isActive ? "Включено" : "Выключено"}
            </button>

            {!selectedId ? (
              <button className="btn ok" onClick={create} disabled={!shopId}>
                Подключить
              </button>
            ) : (
              <button className="btn ok" onClick={updateSelected} disabled={!shopId}>
                Сохранить
              </button>
            )}

            {selectedId ? (
              <button
                className="btn"
                onClick={create}
                disabled={!shopId}
                title="Создать новое подключение с текущими данными"
              >
                Создать как новое
              </button>
            ) : null}
          </div>

          <div className="small">
            {selectedId
              ? "Чтобы создать новое подключение - нажмите «Создать как новое» или «Сбросить форму»."
              : "Если нужно изменить существующее - выберите его слева и нажмите «Сохранить»."}
          </div>
        </div>
      </div>
    </div>
  );
}
