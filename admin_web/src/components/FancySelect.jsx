import React, { useEffect, useMemo, useRef, useState } from "react";

export default function FancySelect({
  value,
  onChange,
  options,
  placeholder = "Выберите...",
  disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  const selectedLabel = useMemo(() => {
    const hit = (options || []).find((o) => String(o.value) === String(value));
    return hit?.label || placeholder;
  }, [options, value, placeholder]);

  useEffect(() => {
    function onDocClick(e) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target)) setOpen(false);
    }
    function onEsc(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, []);

  return (
    <div className={`fancy-select ${disabled ? "disabled" : ""}`} ref={rootRef}>
      <button
        type="button"
        className={`fancy-select-trigger ${open ? "open" : ""}`}
        onClick={() => !disabled && setOpen((v) => !v)}
        disabled={disabled}
      >
        <span className="fancy-select-label">{selectedLabel}</span>
        <span className={`fancy-select-arrow ${open ? "open" : ""}`}>⌄</span>
      </button>

      {open ? (
        <div className="fancy-select-menu">
          {(options || []).map((o) => {
            const active = String(o.value) === String(value);
            return (
              <button
                type="button"
                key={String(o.value)}
                className={`fancy-select-option ${active ? "active" : ""}`}
                onClick={() => {
                  onChange?.(o.value);
                  setOpen(false);
                }}
              >
                {o.label}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
