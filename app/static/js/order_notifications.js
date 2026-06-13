/* order_notifications.js
   Подключи в любой HTML-странице клиента:
   <script src="{{ url_for('static', filename='js/order_notifications.js') }}"></script>
*/

(function () {
  // Не запускаем если пользователь не залогинен (нет элемента-маркера)
  if (!document.body) return;

  // ── Стили уведомления ────────────────────────────────────────────────────
  const STYLES = `
    #order-toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 12px;
      pointer-events: none;
    }
    .order-toast {
      pointer-events: all;
      min-width: 300px;
      max-width: 380px;
      padding: 16px 20px;
      border-radius: 4px;
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      line-height: 1.5;
      box-shadow: 0 8px 32px rgba(0,0,0,0.18);
      display: flex;
      align-items: flex-start;
      gap: 12px;
      animation: toast-in 0.35s ease forwards;
      border-left: 4px solid;
    }
    .order-toast.pending   { background:#fff8e1; border-color:#f59e0b; color:#78350f; }
    .order-toast.preparing { background:#e0f2fe; border-color:#0284c7; color:#0c4a6e; }
    .order-toast.ready     { background:#dcfce7; border-color:#16a34a; color:#14532d; }
    .order-toast .toast-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
    .order-toast .toast-body { flex: 1; }
    .order-toast .toast-title { font-weight: 700; margin-bottom: 2px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }
    .order-toast .toast-close {
      background: none; border: none; cursor: pointer;
      font-size: 16px; opacity: 0.5; padding: 0; line-height: 1;
      flex-shrink: 0; align-self: flex-start;
    }
    .order-toast .toast-close:hover { opacity: 1; }
    @keyframes toast-in {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes toast-out {
      from { opacity: 1; transform: translateY(0); }
      to   { opacity: 0; transform: translateY(16px); }
    }
  `;

  // ── Инициализация контейнера ─────────────────────────────────────────────
  const styleEl = document.createElement("style");
  styleEl.textContent = STYLES;
  document.head.appendChild(styleEl);

  const container = document.createElement("div");
  container.id = "order-toast-container";
  document.body.appendChild(container);

  // ── Показ уведомления ────────────────────────────────────────────────────
  function showToast(orderId, status, message) {
    const icons = { pending: "⏳", preparing: "👨‍🍳", ready: "✅" };
    const titles = { pending: "Order Received", preparing: "Being Prepared", ready: "Order Ready!" };

    const toast = document.createElement("div");
    toast.className = `order-toast ${status}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[status] || "🔔"}</span>
      <div class="toast-body">
        <div class="toast-title">${titles[status] || "Update"} · #${orderId}</div>
        <div>${message}</div>
      </div>
      <button class="toast-close" aria-label="Close">✕</button>
    `;

    toast.querySelector(".toast-close").addEventListener("click", () => removeToast(toast));
    container.appendChild(toast);

    // Автоудаление: ready — 10 сек, остальные — 6 сек
    const timeout = status === "ready" ? 10000 : 6000;
    setTimeout(() => removeToast(toast), timeout);
  }

  function removeToast(toast) {
    toast.style.animation = "toast-out 0.3s ease forwards";
    setTimeout(() => toast.remove(), 300);
  }

  // ── SSE подключение ───────────────────────────────────────────────────────
  function connect() {
    const es = new EventSource("/notifications/order-status");

    es.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        showToast(data.order_id, data.status, data.message);

        // Если заказ готов — воспроизводим звук (если браузер разрешает)
        if (data.status === "ready") playSound();
      } catch (e) {
        console.warn("Notification parse error:", e);
      }
    };

    es.onerror = function () {
      es.close();
      // Переподключение через 5 секунд при обрыве
      setTimeout(connect, 5000);
    };
  }

  // ── Звуковой сигнал при готовности ───────────────────────────────────────
  function playSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {}
  }

  // ── Старт ─────────────────────────────────────────────────────────────────
  connect();
})();