// src/components/DesktopOnly.jsx
import React, { useEffect, useState } from "react";

export default function DesktopOnly({ children }) {
  const [allowed, setAllowed] = useState(true);

  useEffect(() => {
    function check() {
      setAllowed(window.innerWidth >= 1024);
    }

    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  if (!allowed) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: 24,
          background: "#f6f8f4",
        }}
      >
        <div>
          <h2 style={{ marginBottom: 8 }}>Админ-меню недоступно</h2>
          <p style={{ color: "#555" }}>
            Пожалуйста, откройте сайт на компьютере или ноутбуке
          </p>
        </div>
      </div>
    );
  }

  return children;
}
