import React from "react";

export default function Toast({ toast, onClose }) {
  if (!toast) return null;
  return (
    <div className="toast" onClick={onClose} role="button" tabIndex={0}>
      <div className="title">{toast.title}</div>
      <div className="msg">{toast.message}</div>
      <div className="small" style={{marginTop:6}}>Нажми, чтобы закрыть</div>
    </div>
  );
}
