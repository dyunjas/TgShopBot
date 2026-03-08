import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

import Profile from "./Profile.jsx";
import Shops from "./Shops.jsx";
import Pages from "./Pages.jsx";
import Payments from "./Payments.jsx";
import Orders from "./Orders.jsx";
import Transactions from "./Transactions.jsx";
import CatalogManager from "./CatalogManager.jsx";
import Broadcast from "./Broadcast.jsx";
import Operators from "./Operators.jsx";

export default function Dashboard({ onLogout, notify }) {
  const [me, setMe] = useState(null);
  const [tab, setTab] = useState("profile");

  async function loadMe() {
    try {
      const data = await api("/api/admin/me");
      setMe(data);
    } catch (e) {
      notify?.("Ошибка", e.message);
      onLogout?.();
    }
  }

  useEffect(() => {
    loadMe();
  }, []);

  const role = me?.role || "operator";
  const isOperator = role === "operator";
  const isSuper = role === "superadmin";

  useEffect(() => {
    if (isOperator && tab !== "orders" && tab !== "profile") setTab("orders");
  }, [isOperator, tab]);

  const navItems = useMemo(() => {
    const items = [{ key: "profile", label: "Профиль" }];

    if (isOperator) {
      items.push({ key: "orders", label: "Заказы" });
      return items;
    }

    if (isSuper) {
      items.push(
        { key: "orders", label: "Заказы" },
        { key: "transactions", label: "Оплаты" },
        { key: "catalog", label: "Каталог" },
        { key: "broadcast", label: "Рассылка" },
        { key: "operators", label: "Операторы" },
        { key: "shops", label: "Магазины" },
        { key: "pages", label: "Страницы" },
        { key: "payments", label: "Платежные системы" }
      );
    }

    return items;
  }, [isOperator, isSuper]);

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="sidebarBrand">
          <img
            className="sidebarLogo"
            src="/logo.svg"
            alt="DP Shops"
            width="190"
            height="63"
            decoding="async"
          />
        </div>

        <nav className="sidebarNav" aria-label="Разделы админки">
          {navItems.map((x) => (
            <button
              key={x.key}
              type="button"
              className={`navItem ${tab === x.key ? "active" : ""}`}
              aria-current={tab === x.key ? "page" : undefined}
              onClick={() => setTab(x.key)}
            >
              {x.label}
            </button>
          ))}
        </nav>

        <div className="sidebarFooter">
          <button type="button" className="btn danger" onClick={onLogout}>
            Выйти
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="mainInner">
          {tab === "profile" && <Profile notify={notify} />}

          {tab === "orders" && isOperator && <Orders notify={notify} />}

          {tab === "orders" && isSuper && <Orders notify={notify} mode="all" />}

          {tab === "transactions" && isSuper && <Transactions notify={notify} />}

          {tab === "catalog" && isSuper && <CatalogManager notify={notify} />}

          {tab === "broadcast" && isSuper && <Broadcast notify={notify} />}

          {tab === "operators" && isSuper && <Operators notify={notify} />}

          {tab === "shops" && isSuper && <Shops notify={notify} />}

          {tab === "pages" && isSuper && <Pages notify={notify} />}

          {tab === "payments" && isSuper && <Payments notify={notify} />}
        </div>
      </main>
    </div>
  );
}
